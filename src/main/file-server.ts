import express from 'express'
import cors from 'cors'
import { Express } from 'express'
import serveStatic from 'serve-static'

import { join } from 'path'
import { getPluginFolder } from './plugins'

let pluginFileServer: Express
const pluginFileServerURL: string = 'http://127.0.0.1:3000'

/**
 * Starts a file server to serve plugin files
 */
export async function startPluginFileServer(): Promise<void> {
	const pluginFolder = await getPluginFolder()

	pluginFileServer = express()

	pluginFileServer.use(cors())
	pluginFileServer.use(serveStatic(pluginFolder))
	pluginFileServer.listen(3000)
}

export async function stopPluginFileServer(): Promise<void> {
	if ('close' in pluginFileServer && typeof pluginFileServer.close === 'function')
		pluginFileServer?.close()
}

export function getPluginFileServerURL(): string {
	return pluginFileServerURL
}

export function getPluginFileURL(pluginFolder: string, fileRelativePath: string): string {
	const filePath = join(pluginFolder, fileRelativePath)

	const url = new URL(filePath, getPluginFileServerURL())

	return url.toString()
}
