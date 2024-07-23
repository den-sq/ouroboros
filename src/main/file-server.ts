import { join } from 'path'
import { getPluginFolder } from './plugins'
import { ChildProcess, fork } from 'child_process'

let pluginFileServer: ChildProcess
const port = 3000
const pluginFileServerURL: string = `http://127.0.0.1:${port}`

/**
 * Starts a file server to serve plugin files
 */
export async function startPluginFileServer(): Promise<void> {
	const pluginFolder = await getPluginFolder()

	pluginFileServer = fork(join(__dirname, '../../resources/processes/file-server-script.mjs'), [
		pluginFolder,
		`${port}`
	])
}

export async function stopPluginFileServer(): Promise<void> {
	pluginFileServer.kill()
}

export function getPluginFileServerURL(): string {
	return pluginFileServerURL
}

export function getPluginFileURL(pluginFolder: string, fileRelativePath: string): string {
	const filePath = join(pluginFolder, fileRelativePath)

	const url = new URL(filePath, getPluginFileServerURL())

	return url.toString()
}
