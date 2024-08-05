import { BrowserWindow, dialog, IpcMain } from 'electron'
import {
	addLocalPlugin,
	deletePlugin,
	downloadPlugin,
	getPluginFolder,
	initializePlugins,
	PluginDetail,
	restartPlugins,
	sendPluginFolderContents,
	stopAllPlugins
} from '../plugins'
import Watcher from 'watcher'
import { makeExtraWindow } from '../helpers'

const PLUGIN_WINDOW = {
	name: 'Manage Plugins',
	width: 550,
	height: 400,
	path: '#/extras/plugins'
}

export function addPluginEventHandlers(
	ipcMain: IpcMain,
	getPluginDetails: () => PluginDetail[],
	getMainWindow: () => BrowserWindow
): void {
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
		downloadPlugin(url).then(() => {
			// Restart the plugins
			restartPlugins(getPluginDetails(), getMainWindow())
		})
	})

	ipcMain.on('add-local-plugin', async (_, folderPath: string) => {
		// Copy the plugin from the given folder
		addLocalPlugin(folderPath).then(() => {
			// Restart the plugins
			restartPlugins(getPluginDetails(), getMainWindow())
		})
	})

	ipcMain.on('delete-plugin', async (_, pluginFolder: string) => {
		await stopAllPlugins()

		// Delete the plugin folder
		deletePlugin(pluginFolder).then(() => {
			// Restart the plugins
			initializePlugins(getPluginDetails(), getMainWindow())
		})
	})

	ipcMain.on('get-plugin-paths', () => {
		getMainWindow()?.webContents.send('plugin-paths', getPluginDetails())
	})
}
