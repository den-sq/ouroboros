import { is } from '@electron-toolkit/utils'
import { app, BrowserWindow } from 'electron'
import { existsSync } from 'fs'
import fs from 'fs/promises'
import { join } from 'path'
import { parsePluginPackageJSON } from './schemas'

export async function fetchFolderContents(
	folderPath: string
): Promise<{ files: string[]; isFolder: boolean[] }> {
	try {
		// https://nodejs.org/api/fs.html#fspromisesreaddirpath-options
		const files = await fs.readdir(folderPath)

		// Filter out hidden files
		// https://stackoverflow.com/questions/18973655/how-to-ignore-hidden-files-in-fs-readdir-result
		// eslint-disable-next-line no-useless-escape
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

export async function saveFile({ folder, name, data }): Promise<boolean> {
	try {
		// Create the folder if it doesn't exist
		await fs.mkdir(folder, { recursive: true })

		await fs.writeFile(join(folder, name), data)
		return true
	} catch (error) {
		return false
	}
}

export async function readFile({ folder, name }): Promise<string> {
	try {
		const data = await fs.readFile(join(folder, name), 'utf-8')
		return data
	} catch (error) {
		return ''
	}
}

export function makeExtraWindow({
	width,
	height,
	path,
	name
}: {
	width: number
	height: number
	path: string
	name: string
}): BrowserWindow {
	const managePluginsWindow = new BrowserWindow({
		width: width,
		height: height,
		minWidth: width,
		minHeight: height,
		autoHideMenuBar: true,
		webPreferences: {
			preload: join(__dirname, '../preload/index.js'),
			sandbox: false
		},
		title: name
	})

	// Open the plugin page in a new window
	if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
		managePluginsWindow.loadURL(process.env['ELECTRON_RENDERER_URL'] + path)
	} else {
		managePluginsWindow.loadFile(join(__dirname, '../renderer/index.html' + path))
	}

	return managePluginsWindow
}

export async function getPluginFolder(): Promise<string> {
	const userData = app.getPath('userData')
	const pluginFolder = join(userData, 'plugins')

	// Create the plugin folder if it doesn't exist
	await fs.mkdir(pluginFolder, { recursive: true })

	return pluginFolder
}

export async function getPluginList(pluginFolder: string): Promise<{ name: string; id: string }[]> {
	const result = await fetchFolderContents(pluginFolder)
	const folders = result.files.filter((_, i) => result.isFolder[i])

	const pluginFolderContents: { name: string; id: string }[] = []

	for (const folder of folders) {
		const parentFolder = join(pluginFolder, folder)
		const pathToPackageJSON = join(parentFolder, 'package.json')

		// Check if the folder contains a package.json file
		if (!existsSync(pathToPackageJSON)) {
			continue
		}

		const packageJSON = await readFile({ folder: parentFolder, name: 'package.json' })

		// Check if the package.json file is valid
		const parsedJSON = parsePluginPackageJSON(packageJSON)

		if (typeof parsedJSON === 'string') {
			console.error(parsedJSON)
			continue
		}

		// Check if the main script file exists
		const pathToMain = join(parentFolder, parsedJSON.main)

		if (!existsSync(pathToMain)) {
			console.error(`Main script file not found: ${pathToMain}`)
			continue
		}

		// Check if the styles file exists
		if (parsedJSON.styles) {
			const pathToStyles = join(parentFolder, parsedJSON.styles)

			if (!existsSync(pathToStyles)) {
				console.error(`Styles file not found: ${pathToStyles}`)
				continue
			}
		}

		// Check if the Dockerfile exists
		if (parsedJSON.dockerfile) {
			const pathToDockerfile = join(parentFolder, parsedJSON.dockerfile)

			if (!existsSync(pathToDockerfile)) {
				console.error(`Dockerfile not found: ${pathToDockerfile}`)
				continue
			}
		}

		pluginFolderContents.push({ name: parsedJSON.pluginName, id: parsedJSON.name })
	}

	return pluginFolderContents
}

export async function sendPluginFolderContents(
	pluginWindow: BrowserWindow | null,
	pluginFolder: string
): Promise<void> {
	const pluginFolderContents = await getPluginList(pluginFolder)

	pluginWindow?.webContents.send('plugin-folder-contents', pluginFolderContents)
}
