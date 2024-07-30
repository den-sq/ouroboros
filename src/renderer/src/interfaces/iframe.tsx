import {
	IFrameMessage,
	IFrameMessageSchema,
	ReadFileRequestSchema,
	ReadFileResponse,
	RegisterIFrameSchema,
	SaveFileRequestSchema,
	SendDirectoryContents
} from '@renderer/schemas/iframe-message-schema'
import { safeParse } from 'valibot'
import { readFile, writeFile } from './file'
import { useContext, useEffect, useState } from 'react'
import { DirectoryContext } from '@renderer/contexts/DirectoryContext'

export function IFrameManager(): JSX.Element {
	// Define allowed origins
	const allowedOrigins: string[] = ['http://localhost', 'http://127.0.0.1', 'http://0.0.0.0']

	// Store references to iframes
	const [iframes, setIframes] = useState(new Map<string, MessageEventSource>())

	const updateIframes = async (
		source: MessageEventSource,
		data: IFrameMessage
	): Promise<void> => {
		const result = safeParse(RegisterIFrameSchema, data)

		if (!result.success) return

		const { pluginName } = result.output.data

		setIframes((prev) => new Map([...prev, [pluginName, source]]))
	}

	// Define the handlers for the different message types
	const handlers: {
		[key: string]: (source: MessageEventSource, data: IFrameMessage) => Promise<void>
	} = {
		'read-file': handleReadFileRequest,
		'save-file': handleSaveFileRequest,
		'register-plugin': updateIframes
	}

	const listener = (event: MessageEvent): void => {
		const origin = event.origin

		// Validate the origin of the request
		if (!listContainsStartsWith(allowedOrigins, origin)) return

		const request = event.data

		// Validate the request format
		const messageParse = safeParse(IFrameMessageSchema, request)

		if (!messageParse.success) return

		const message = messageParse.output

		if (!event.source) return

		// Asynchronously handle the message
		if (message.type in handlers) {
			handlers[message.type](event.source, message).catch(console.error)
		}
	}

	// Create listener for messages from any iframe
	window.addEventListener('message', listener)

	// Access the directory context
	const data = useContext(DirectoryContext)

	useEffect(() => {
		if (!data) return

		const message: SendDirectoryContents = {
			type: 'send-directory-contents',
			data: {
				directoryPath: data.directoryPath,
				directoryName: data.directoryName,
				files: data.files,
				isFolder: data.isFolder
			}
		}

		// Send the directory info to the iframes
		iframes.forEach((iframe) => {
			iframe.postMessage(message, {
				targetOrigin: '*'
			})
		})
	}, [data, iframes])

	useEffect(() => {
		return (): void => {
			window.removeEventListener('message', listener)
		}
	}, [])

	return <></>
}

async function handleReadFileRequest(
	source: MessageEventSource,
	data: IFrameMessage
): Promise<void> {
	// Validate the data format
	const parseResult = safeParse(ReadFileRequestSchema, data)

	if (!parseResult.success) return

	const readFileRequest = parseResult.output

	// Read the file contents
	const filePath = readFileRequest.data.filePath
	let contents = ''

	try {
		contents = await readFile('', filePath)
	} catch (e) {
		console.error(e)
		return
	}

	// Send the file contents back to the iframe
	const response: ReadFileResponse = {
		type: 'read-file-response',
		data: {
			filePath,
			contents
		}
	}

	// Send the response to the iframe
	source.postMessage(response, {
		targetOrigin: '*'
	})
}

async function handleSaveFileRequest(_: MessageEventSource, data: IFrameMessage): Promise<void> {
	// Validate the data format
	const parseResult = safeParse(SaveFileRequestSchema, data)

	if (!parseResult.success) return

	const readFileRequest = parseResult.output

	const filePath = readFileRequest.data.filePath
	const fileContents = readFileRequest.data.contents

	try {
		await writeFile('', filePath, fileContents)
	} catch (e) {
		console.error(e)
		return
	}
}

function listContainsStartsWith(startsWith: string[], text: string): boolean {
	for (const item of startsWith) {
		if (text.startsWith(item)) {
			return true
		}
	}

	return false
}
