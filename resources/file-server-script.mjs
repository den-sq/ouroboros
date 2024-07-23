/* eslint-disable @typescript-eslint/explicit-function-return-type */
import express from 'express'
import cors from 'cors'
import serveStatic from 'serve-static'

let pluginFileServer
/**
 * Starts a file server to serve plugin files
 */
async function startPluginFileServer(pluginFolder, port) {
	pluginFileServer = express()

	pluginFileServer.use(cors())
	pluginFileServer.use(serveStatic(pluginFolder))
	pluginFileServer.listen(port)
}

export function stopPluginFileServer() {
	if (
		pluginFileServer &&
		'close' in pluginFileServer &&
		typeof pluginFileServer.close === 'function'
	)
		pluginFileServer?.close()
}

if (process.argv.length > 3) {
	const pluginFolder = process.argv[2]
	const port = parseInt(process.argv[3])

	startPluginFileServer(pluginFolder, port)
} else {
	console.error(
		`Incorrect usage of file-server-script.js. Expected 2 arguments but got ${process.argv.length - 2}`
	)
}

process.on('exit', () => {
	stopPluginFileServer()
})
