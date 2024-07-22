import { BrowserWindow, dialog, ipcMain } from 'electron'
import Watcher from 'watcher'
import { fetchFolderContents, makeExtraWindow, readFile, saveFile } from './helpers'
import { is } from '@electron-toolkit/utils'
import { basename, join } from 'path'
import {
	addLocalPlugin,
	deletePlugin,
	downloadPlugin,
	getPluginFolder,
	PluginDetail,
	sendPluginFolderContents
} from './plugins'
import { PLUGIN_WINDOW } from '.'

export function handleEvents({
	getMainWindow,
	getPluginDetails
}: {
	getMainWindow: () => BrowserWindow
	getPluginDetails: () => PluginDetail[]
}): void {
	let subscription: Watcher | null = null

	// Fetch the contents of the given folder
	ipcMain.handle('fetch-folder-contents', async (_, folderPath: string) => {
		if (folderPath === '' || folderPath === undefined || folderPath === null)
			return { files: [], isFolder: [] }

		if (subscription) {
			subscription.close()
			subscription = null
		}

		// Send updates to the renderer when the folder contents change
		subscription = new Watcher(folderPath)

		subscription.on('all', async () => {
			const result = await fetchFolderContents(folderPath)
			getMainWindow()?.webContents.send('folder-contents-update', result)
		})

		return await fetchFolderContents(folderPath)
	})

	ipcMain.on('get-is-dev', () => {
		getMainWindow()?.webContents.send('is-dev', is.dev)
	})

	// Save a string to a file
	ipcMain.handle('save-file', async (_, args) => {
		return await saveFile(args)
	})

	// Join two paths
	ipcMain.handle('join-path', (_, { folder, name }) => {
		return join(folder, name)
	})

	// Get base name of a path
	ipcMain.handle('basename-path', (_, { folder }) => {
		return basename(folder)
	})

	// Read the contents of a file as a string
	ipcMain.handle('read-file', async (_, args) => {
		return await readFile(args)
	})

	let pluginSubscription: Watcher | null = null
	let pluginWindow: BrowserWindow | null = null

	ipcMain.on('manage-plugins', async () => {
		// Make new window for mananging plugins
		pluginWindow = makeExtraWindow(PLUGIN_WINDOW)

		pluginWindow.on('close', () => {
			if (pluginSubscription) {
				pluginSubscription.close()
				pluginSubscription = null
			}
		})
	})

	ipcMain.on('get-plugin-folder-contents', async () => {
		// Get the path to the plugin folder
		const pluginFolder = await getPluginFolder()

		if (pluginFolder === '') {
			dialog.showErrorBox('Plugin Folder Not Found', 'The plugin folder was not found.')
			return
		}

		if (pluginSubscription) {
			pluginSubscription.close()
			pluginSubscription = null
		}

		pluginSubscription = new Watcher(pluginFolder)

		// Send updates to the renderer when the folder contents change
		pluginSubscription.on('all', async () => {
			sendPluginFolderContents(pluginWindow, pluginFolder)
		})

		// Send the contents of the plugin folder to the renderer
		sendPluginFolderContents(pluginWindow, pluginFolder)
	})

	ipcMain.on('download-plugin', async (_, url: string) => {
		// Download the plugin from the given github URL
		downloadPlugin(url)
	})

	ipcMain.on('add-local-plugin', async (_, folderPath: string) => {
		// Copy the plugin from the given folder
		addLocalPlugin(folderPath)
	})

	ipcMain.on('delete-plugin', async (_, pluginFolder: string) => {
		deletePlugin(pluginFolder)
	})

	ipcMain.on('get-plugin-paths', () => {
		getMainWindow()?.webContents.send('plugin-paths', getPluginDetails())
	})
}
