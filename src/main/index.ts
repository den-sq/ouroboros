import { app, shell, BrowserWindow, Menu } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'

import { ChildProcess, execFile } from 'child_process'
import { existsSync } from 'fs'

import { BACKGROUND_COLOR } from '../main/helpers'
import { initializePlugins, PluginDetail, stopAllPlugins } from './plugins'
import { startPluginFileServer, stopPluginFileServer } from './servers/file-server'
import { handleEvents } from './events'
import { makeMenu } from './menu'
import {
	startMainServerDevelopment,
	startMainServerProduction,
	stopMainServerDevelopment,
	stopMainServerProduction
} from './servers/main-server'
import { startVolumeServer, stopVolumeServer } from './servers/volume-server'

export const PLUGIN_WINDOW = {
	name: 'Manage Plugins',
	width: 550,
	height: 400,
	path: '#/extras/plugins'
}

let mainWindow: Electron.BrowserWindow
let mainServer: ChildProcess

const pluginDetails: PluginDetail[] = []

const getMainWindow = (): BrowserWindow => mainWindow
const getPluginDetails = (): PluginDetail[] => pluginDetails

function createWindow(): void {
	mainWindow = new BrowserWindow({
		show: false,
		...(process.platform === 'linux' ? { icon } : {}),
		webPreferences: {
			preload: join(__dirname, '../preload/index.js'),
			sandbox: false
		},
		title: 'Ouroboros',
		backgroundColor: BACKGROUND_COLOR
	})

	Menu.setApplicationMenu(makeMenu(mainWindow))

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
	// Note: this is no longer the default behavior
	// but it still works if the server is present
	if (!is.dev) {
		const serverPath = join(
			__dirname,
			`../../resources/ouroboros-server${process.platform === 'win32' ? '.exe' : ''}`
		)

		// Check that the server exists
		if (!existsSync(serverPath)) {
			console.error('Server not found')
		} else {
			mainServer = execFile(serverPath)

			mainServer.stderr?.on('data', (data) => {
				console.error(data.toString())
			})
			mainServer.stdout?.on('data', (data) => {
				console.log(data.toString())
			})
		}
	}

	// Start all plugins
	initializePlugins(pluginDetails, mainWindow)

	startPluginFileServer()

	// Start the main server
	if (is.dev) {
		startMainServerDevelopment()
	} else {
		startMainServerProduction()
	}

	// Start the docker volume server
	startVolumeServer()
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

	handleEvents({
		getMainWindow,
		getPluginDetails
	})

	createWindow()

	app.on('activate', function () {
		// On macOS it's common to re-create a window in the app when the
		// dock icon is clicked and there are no other windows open.
		if (BrowserWindow.getAllWindows().length === 0) createWindow()
	})
})

app.on('window-all-closed', async () => {
	mainServer?.kill()

	try {
		// Stop all plugins and other servers before quitting
		await Promise.all([
			stopAllPlugins(),
			stopPluginFileServer(),
			stopVolumeServer(),
			is.dev && stopMainServerDevelopment(),
			!is.dev && stopMainServerProduction()
		])
	} catch (error) {
		console.error('An error occurred while stopping the servers:', error)
	}

	app.quit()
})
