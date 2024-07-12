import {
	app,
	shell,
	BrowserWindow,
	ipcMain,
	Menu,
	dialog,
	MenuItemConstructorOptions
} from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'

import fs from 'fs/promises'
import { ChildProcess, execFile } from 'child_process'
import { existsSync } from 'fs'
import Watcher from 'watcher'

let mainWindow: Electron.BrowserWindow
let mainServer: ChildProcess

function createWindow(): void {
	mainWindow = new BrowserWindow({
		show: false,
		autoHideMenuBar: true,
		...(process.platform === 'linux' ? { icon } : {}),
		webPreferences: {
			preload: join(__dirname, '../preload/index.js'),
			sandbox: false
		},
		title: 'Ouroboros'
	})

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

	const menu = Menu.buildFromTemplate(template as MenuItemConstructorOptions[])

	Menu.setApplicationMenu(menu)

	mainWindow.on('ready-to-show', () => {
		mainWindow.maximize()
		mainWindow.focus()
	})

	mainWindow.webContents.setWindowOpenHandler((details) => {
		shell.openExternal(details.url)
		return { action: 'deny' }
	})

	// HMR for renderer base on electron-vite cli.
	// Load the remote URL for development or the local html file for production.
	if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
		mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
	} else {
		mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
	}

	// Run the Python Server with execFile
	if (!is.dev) {
		const serverPath = join(
			__dirname,
			`../../resources/ouroboros-server${process.platform === 'win32' ? '.exe' : ''}`
		)

		// Check that the server exists
		if (!existsSync(serverPath)) {
			console.error('Server not found')
			return
		}

		mainServer = execFile(serverPath)

		mainServer.stderr?.on('data', (data) => {
			console.error(data.toString())
		})
		mainServer.stdout?.on('data', (data) => {
			console.log(data.toString())
		})
	}
}

app.whenReady().then(() => {
	// Set app user model id for windows
	electronApp.setAppUserModelId('com.wegold')

	// Default open or close DevTools by F12 in development
	// and ignore CommandOrControl + R in production.
	// see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
	app.on('browser-window-created', (_, window) => {
		optimizer.watchWindowShortcuts(window)
	})

	async function fetchFolderContents(
		folderPath: string
	): Promise<{ files: string[]; isFolder: boolean[] }> {
		try {
			// https://nodejs.org/api/fs.html#fspromisesreaddirpath-options
			const files = await fs.readdir(folderPath)

			// Filter out hidden files
			// https://stackoverflow.com/questions/18973655/how-to-ignore-hidden-files-in-fs-readdir-result
			const noHidden = files.filter((item) => !/(^|\/)\.[^\/\.]/g.test(item))

			// Determine if each file is a folder or a file
			const isFolder = await Promise.all(
				noHidden.map(async (file) => {
					try {
						const stats = await fs.stat(join(folderPath, file))
						return stats.isDirectory()
					} catch (error) {
						return false
					}
				})
			)

			return { files: noHidden, isFolder: isFolder }
		} catch (error) {
			return { files: [], isFolder: [] }
		}
	}

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
			mainWindow?.webContents.send('folder-contents-update', result)
		})

		return await fetchFolderContents(folderPath)
	})

	// Save a string to a file
	ipcMain.handle('save-file', async (_, { folder, name, data }) => {
		try {
			// Create the folder if it doesn't exist
			await fs.mkdir(folder, { recursive: true })

			await fs.writeFile(join(folder, name), data)
			return true
		} catch (error) {
			return false
		}
	})

	// Join two paths
	ipcMain.handle('join-path', (_, { folder, name }) => {
		return join(folder, name)
	})

	// Read the contents of a file as a string
	ipcMain.handle('read-file', async (_, { folder, name }) => {
		try {
			const data = await fs.readFile(join(folder, name), 'utf-8')
			return data
		} catch (error) {
			return ''
		}
	})

	createWindow()

	app.on('activate', function () {
		// On macOS it's common to re-create a window in the app when the
		// dock icon is clicked and there are no other windows open.
		if (BrowserWindow.getAllWindows().length === 0) createWindow()
	})
})

app.on('window-all-closed', () => {
	app.quit()

	mainServer?.kill()
})
