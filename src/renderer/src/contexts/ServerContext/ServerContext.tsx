import { createContext, useEffect, useState } from 'react'

const DEFAULT_SERVER_URL = 'http://127.0.0.1:8000'
const ID_PROPERTY_NAME = 'task_id'

export type ServerContextValue = {
	baseURL: string
	activeID: string | null
	connected: boolean
	useFetch: (
		relativeURL: string,
		query?: Record<string, any>,
		runFetch?: boolean,
		options?: RequestInit
	) => {
		data: object | null
		loading: boolean
		error: { status: boolean; message: string } | null
	}
	useStream: (
		relativeURL: string,
		query?: Record<string, any>,
		runStream?: boolean
	) => { data: object | null; done: boolean; error: { status: boolean; message: string } | null }
}

export const ServerContext = createContext<ServerContextValue>(null as any)

function ServerProvider({ baseURL = DEFAULT_SERVER_URL, idPropName = ID_PROPERTY_NAME, children }) {
	const [activeID, setActiveID] = useState<string | null>(null)

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

	const getFullURL = (relativeURL: string, query = {}) => {
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
	}

	// https://github.com/franlol/useFetch
	function useFetch(relativeURL: string, query = {}, runFetch = true, options = {}) {
		const [data, setData] = useState({})
		const [loading, setLoading] = useState(false)
		const [error, setError] = useState({ status: false, message: '' })

		useEffect(() => {
			;(async () => {
				if (!runFetch) return

				setLoading(true)
				try {
					const response = await fetch(getFullURL(relativeURL, query), options)
					if (!response.ok) throw new Error('Error fetching data.')
					const json = await response.json()
					setData(json)
					setLoading(false)

					// Update the active ID if it is present in the response
					if (idPropName && idPropName in json) {
						setActiveID(json[idPropName])
					}
				} catch (error) {
					let message = 'Unknown error occurred while fetching data.'
					if (error instanceof Error) {
						message = error.message
					}
					setError({ status: true, message: message })
					setLoading(false)
				}
			})()
		}, [runFetch])
		return { data, loading, error }
	}

	function useStream(relativeURL: string, query = {}, runStream = true) {
		const [data, setData] = useState({})
		const [done, setDone] = useState(false)
		const [error, setError] = useState({ status: false, message: '' })

		useEffect(() => {
			if (!runStream) return

			const eventSource = new EventSource(getFullURL(relativeURL, query))

			eventSource.addEventListener('update_event', (event) => {
				setData(JSON.parse(event.data))
			})

			eventSource.addEventListener('done_event', (event) => {
				setData(JSON.parse(event.data))
				setDone(true)
				eventSource.close()
			})

			eventSource.addEventListener('error_event', (event) => {
				const data = JSON.parse(event.data)

				setData(data)

				let error = 'Unknown error occurred while streaming data.'

				if ('error' in data && data.error) {
					error = data.error
				}

				setError({ status: true, message: error })
				setDone(true)
				eventSource.close()
			})

			return () => {
				eventSource.close()
			}
		}, [runStream])

		return { data, done, error }
	}

	return (
		<ServerContext.Provider value={{ baseURL, activeID, connected, useFetch, useStream }}>
			{children}
		</ServerContext.Provider>
	)
}

export default ServerProvider
