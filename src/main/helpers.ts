import { is } from '@electron-toolkit/utils'
import { app, BrowserWindow } from 'electron'
import { existsSync } from 'fs'
import fs from 'fs/promises'
import { join } from 'path'
import { parsePluginPackageJSON } from './schemas'
import { downloadRelease } from '@terascope/fetch-github-release'

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

export async function getPluginList(
	pluginFolder: string
): Promise<{ name: string; id: string; folder: string }[]> {
	const result = await fetchFolderContents(pluginFolder)
	const folders = result.files.filter((_, i) => result.isFolder[i])

	const pluginFolderContents: { name: string; id: string; folder: string }[] = []

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

		pluginFolderContents.push({
			name: parsedJSON.pluginName,
			id: parsedJSON.name,
			folder: parentFolder
		})
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

export async function deletePlugin(pluginFolder: string): Promise<void> {
	await fs.rm(pluginFolder, { recursive: true })
}

export async function addLocalPlugin(pluginFolder: string): Promise<void> {
	const pluginFolderPath = await getPluginFolder()

	// Get the name of the plugin folder
	const pluginFolderSplit = pluginFolder.split('/')
	const pluginFolderName = pluginFolderSplit[pluginFolderSplit.length - 1]

	// Create the plugin folder if it doesn't exist
	const targetFolder = join(pluginFolderPath, pluginFolderName)
	await fs.mkdir(targetFolder, { recursive: true })

	// Copy the folder from the given path to the plugin folder
	await fs.cp(pluginFolder, targetFolder, { recursive: true })
}

/**
 * Downloads the plugin from the given github releases URL
 */
export async function downloadPlugin(url: string): Promise<void> {
	// Determine if the URL is a github releases URL or a github repository URL
	const urlSplit = url.split('/')
	const isReleasesURL = urlSplit.includes('releases')

	// If the URL is not a releases URL, make sure it is a github repository URL
	if (!isReleasesURL) {
		const isGithub = urlSplit.includes('github.com')

		if (!isGithub) {
			console.error('URL is not a github repository URL')
			return
		}
	}

	// If the URL is a github repository URL, get the releases URL
	const releasesURL = isReleasesURL ? url : new URL('/releases/', url).toString()

	// Get the user and repo from the URL
	const user = releasesURL.split('/')[3]
	const repo = releasesURL.split('/')[4]

	const outputDir = join(app.getPath('temp'), `${user}-${repo}`)
	const leaveZipped = false
	const disableLogging = false

	try {
		await downloadRelease(
			user,
			repo,
			outputDir,
			() => true,
			() => true,
			leaveZipped,
			disableLogging
		)
	} catch (error) {
		console.error(error)
		return
	}

	if (existsSync(outputDir)) {
		await addLocalPlugin(outputDir)

		// Delete the downloaded release
		await fs.rm(outputDir, { recursive: true })
	}
}
