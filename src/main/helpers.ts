import { is } from '@electron-toolkit/utils'
import { BrowserWindow } from 'electron'
import fs from 'fs/promises'
import { join } from 'path'

export const BACKGROUND_COLOR = '#2d2e3c'

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
	const extraWindow = new BrowserWindow({
		width: width,
		height: height,
		minWidth: width,
		minHeight: height,
		autoHideMenuBar: true,
		webPreferences: {
			preload: join(__dirname, '../preload/index.js'),
			sandbox: false
		},
		title: name,
		backgroundColor: BACKGROUND_COLOR
	})

	// Open the plugin page in a new window
	if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
		extraWindow.loadURL(process.env['ELECTRON_RENDERER_URL'] + path)
	} else {
		const fullPath = `file://${join(__dirname, '../renderer/index.html' + path)}`
		extraWindow.loadURL(fullPath)
	}

	return extraWindow
}
