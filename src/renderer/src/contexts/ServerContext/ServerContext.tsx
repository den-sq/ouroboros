import { createContext, useCallback, useEffect, useState } from 'react'

const DEFAULT_SERVER_URL = 'http://127.0.0.1:8000'
// const ID_PROPERTY_NAME = 'task_id'

export type ServerContextValue = {
	baseURL: string
	connected: boolean
	fetchResults: object | null
	fetchError: { status: boolean; message: string }
	streamResults: object | null
	streamError: { status: boolean; message: string }
	streamDone: boolean
	performFetch: (
		relativeURL: string,
		query?: Record<string, any>,
		options?: RequestInit
	) => Promise<void>
	performStream: (relativeURL: string, query?: Record<string, any>) => void
}

export const ServerContext = createContext<ServerContextValue>(null as any)

function useServerContextProvider(baseURL = DEFAULT_SERVER_URL) {
	const [fetchResults, setFetchResults] = useState<object | null>(null)
	const [fetchError, setFetchError] = useState({ status: false, message: '' })

	const [streamResults, setStreamResults] = useState<object | null>(null)
	const [streamError, setStreamError] = useState({ status: false, message: '' })
	const [streamDone, setStreamDone] = useState(false)

	const [connected, setConnected] = useState(false)
	const retryDelay = 5000 // Delay between checks in milliseconds

	useEffect(() => {
		const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

		let isMounted = true // Flag to manage cleanup

		const checkServerStatus = async () => {
			while (isMounted) {
				try {
					const response = await fetch(baseURL)
					if (response.ok) {
						setConnected(true)
					} else {
						setConnected(false)
					}
				} catch (error) {
					setConnected(false) // Ensure disconnected state on error
				}
				await delay(retryDelay) // Wait before next check
			}
		}

		checkServerStatus()

		// Cleanup function to stop polling when component unmounts
		return () => {
			isMounted = false
		}
	}, [baseURL, retryDelay])

	const getFullURL = useCallback(
		(relativeURL: string, query = {}) => {
			// Append query parameters to the URL
			const searchParams = Object.keys(query)
				.map((key) => {
					const value = query[key]
					return `${key}=${value}`
				})
				.join('&')

			if (searchParams.toString().length > 0) {
				relativeURL += '?' + searchParams.toString()
			}

			return new URL(relativeURL, baseURL).toString()
		},
		[baseURL]
	)

	const performFetch = useCallback(
		async (relativeURL: string, query: Record<string, any> = {}, options: RequestInit = {}) => {
			const fullURL = getFullURL(relativeURL, query)

			// Reset the fetch error state
			setFetchError({ status: false, message: '' })

			try {
				const response = await fetch(fullURL, options)
				const data = await response.json()
				setFetchResults(data)
			} catch (error) {
				const message =
					error instanceof Error
						? error.message
						: 'Unknown error occurred while fetching data.'
				setFetchError({ status: true, message: message })
			}
		},
		[getFullURL]
	)

	const performStream = useCallback(
		(relativeURL: string, query: Record<string, any> = {}) => {
			const fullURL = getFullURL(relativeURL, query)
			const eventSource = new EventSource(fullURL)

			eventSource.addEventListener('open', () => {
				setStreamResults(null)
				setStreamDone(false)
				setStreamError({ status: false, message: '' })
			})

			eventSource.addEventListener('update_event', (event) => {
				const data = JSON.parse(event.data)
				setStreamResults(data)
			})

			eventSource.addEventListener('done_event', (event) => {
				const data = JSON.parse(event.data)
				setStreamResults(data)
				setStreamDone(true)
				eventSource.close()
			})

			eventSource.addEventListener('error_event', (event) => {
				const data = JSON.parse(event.data)
				setStreamResults(data)

				let error = 'Unknown error occurred while streaming data.'

				if ('error' in data && data.error && typeof data.error === 'string') {
					error = data.error
				}

				setStreamError({ status: true, message: error })
				setStreamDone(true)
				eventSource.close()
			})

			eventSource.addEventListener('error', (error) => {
				const message =
					error instanceof Error
						? error.message
						: 'Unknown error occurred while streaming data.'
				setStreamError({ status: true, message: message })
				eventSource.close()
			})

			return () => {
				eventSource.close()
			}
		},
		[getFullURL]
	)

	return {
		baseURL,
		fetchResults,
		streamResults,
		performFetch,
		performStream,
		fetchError,
		streamError,
		streamDone,
		connected
	}
}

function ServerProvider({ baseURL = DEFAULT_SERVER_URL, children }) {
	const serverContextValue = useServerContextProvider(baseURL)

	return <ServerContext.Provider value={serverContextValue}>{children}</ServerContext.Provider>
}

export default ServerProvider
