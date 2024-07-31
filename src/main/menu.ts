import {
	app,
	BrowserWindow,
	dialog,
	ipcMain,
	Menu,
	MenuItemConstructorOptions,
	shell
} from 'electron'

export function makeMenu(mainWindow: BrowserWindow): Menu {
	const isMac = process.platform === 'darwin'

	const template = [
		// { role: 'appMenu' }
		...(isMac
			? [
					{
						label: app.name,
						submenu: [
							{ role: 'about' },
							{ type: 'separator' },
							{ role: 'services' },
							{ type: 'separator' },
							{ role: 'hide' },
							{ role: 'hideOthers' },
							{ role: 'unhide' },
							{ type: 'separator' },
							{ role: 'quit' }
						]
					}
				]
			: []),
		// { role: 'fileMenu' }
		{
			label: 'File',
			submenu: [
				{
					label: 'Open Folder',
					click: async (): Promise<void> => {
						const result = await dialog.showOpenDialog(mainWindow, {
							properties: ['openDirectory']
						})
						if (!result.canceled) {
							mainWindow.webContents.send('selected-folder', result.filePaths[0])
						}
					}
				},
				{ type: 'separator' },
				{
					label: 'Manage Plugins',
					click: (): void => {
						ipcMain.emit('manage-plugins')
					}
				},
				{ type: 'separator' },
				isMac ? { role: 'close' } : { role: 'quit' }
			]
		},
		// { role: 'editMenu' }
		{
			label: 'Edit',
			submenu: [
				{ role: 'undo' },
				{ role: 'redo' },
				{ type: 'separator' },
				{ role: 'cut' },
				{ role: 'copy' },
				{ role: 'paste' },
				...(isMac
					? [
							{ role: 'pasteAndMatchStyle' },
							{ role: 'delete' },
							{ role: 'selectAll' },
							{ type: 'separator' },
							{
								label: 'Speech',
								submenu: [{ role: 'startSpeaking' }, { role: 'stopSpeaking' }]
							}
						]
					: [{ role: 'delete' }, { type: 'separator' }, { role: 'selectAll' }])
			]
		},
		// { role: 'viewMenu' }
		{
			label: 'View',
			submenu: [
				{ role: 'reload' },
				{ role: 'forceReload' },
				{ role: 'toggleDevTools' },
				{ type: 'separator' },
				{ role: 'resetZoom' },
				{ role: 'zoomIn' },
				{ role: 'zoomOut' },
				{ type: 'separator' },
				{ role: 'togglefullscreen' }
			]
		},
		// { role: 'windowMenu' }
		{
			label: 'Window',
			submenu: [
				{ role: 'minimize' },
				{ role: 'zoom' },
				...(isMac
					? [
							{ type: 'separator' },
							{ role: 'front' },
							{ type: 'separator' },
							{ role: 'window' }
						]
					: [{ role: 'close' }])
			]
		},
		{
			role: 'help',
			submenu: [
				{
					label: 'Learn More',
					click: async (): Promise<void> => {
						await shell.openExternal('https://github.com/We-Gold/ouroboros')
					}
				},
				{
					label: 'Report Issue',
					click: async (): Promise<void> => {
						await shell.openExternal('https://github.com/We-Gold/ouroboros/issues')
					}
				}
			]
		}
	]

	return Menu.buildFromTemplate(template as MenuItemConstructorOptions[])
}
