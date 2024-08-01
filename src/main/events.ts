import { BrowserWindow, ipcMain } from 'electron'
import { is } from '@electron-toolkit/utils'
import { PluginDetail } from './plugins'
import { addFSEventHandlers } from './event-handlers/filesystem'
import { addPluginEventHandlers } from './event-handlers/plugins'

export function handleEvents({
	getMainWindow,
	getPluginDetails
}: {
	getMainWindow: () => BrowserWindow
	getPluginDetails: () => PluginDetail[]
}): void {
	// Add filesystem event handlers
	addFSEventHandlers(ipcMain, getMainWindow)

	ipcMain.on('get-is-dev', () => {
		getMainWindow()?.webContents.send('is-dev', is.dev)
	})

	// Add plugin event handlers
	addPluginEventHandlers(ipcMain, getPluginDetails, getMainWindow)
}
