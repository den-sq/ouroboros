import { app, BrowserWindow, dialog } from 'electron'
import { existsSync } from 'fs'
import fs from 'fs/promises'
import { join } from 'path'
import { parsePluginPackageJSON, PluginPackageJSON } from './schemas'
import { downloadRelease } from '@terascope/fetch-github-release'
import { fetchFolderContents, readFile } from './helpers'
import { buildDockerCompose, checkDocker, startDockerCompose, stopDockerCompose } from './docker'
import { getPluginFileURL } from './file-server'

export async function getPluginFolder(): Promise<string> {
	const userData = app.getPath('userData')
	const pluginFolder = join(userData, 'plugins')

	// Create the plugin folder if it doesn't exist
	await fs.mkdir(pluginFolder, { recursive: true })

	return pluginFolder
}

export async function getPluginList(
	pluginFolder: string,
	includeJSON = false
): Promise<
	{ name: string; id: string; folder: string; folderName: string; json?: PluginPackageJSON }[]
> {
	const result = await fetchFolderContents(pluginFolder)
	const folders = result.files.filter((_, i) => result.isFolder[i])

	const pluginFolderContents: {
		name: string
		id: string
		folder: string
		folderName: string
		json?: PluginPackageJSON
	}[] = []

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

		// Check if the index html file exists
		const pathToIndex = join(parentFolder, parsedJSON.index)

		if (!existsSync(pathToIndex)) {
			console.error(`Index html file not found: ${pathToIndex}`)
			continue
		}

		// Check if the Docker Compose exists
		if (parsedJSON.dockerCompose) {
			const pathToDockerCompose = join(parentFolder, parsedJSON.dockerCompose)

			if (!existsSync(pathToDockerCompose)) {
				console.error(`Dockerfile not found: ${pathToDockerCompose}`)
				continue
			}
		}

		if (includeJSON) {
			pluginFolderContents.push({
				name: parsedJSON.pluginName,
				id: parsedJSON.name,
				folder: parentFolder,
				folderName: folder,
				json: parsedJSON
			})
		} else {
			pluginFolderContents.push({
				name: parsedJSON.pluginName,
				id: parsedJSON.name,
				folder: parentFolder,
				folderName: folder
			})
		}
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

	// Get the package.json file
	const pathToPackageJSON = join(pluginFolder, 'package.json')

	// Check if the folder contains a package.json file
	if (!existsSync(pathToPackageJSON)) {
		return
	}

	const packageJSON = await readFile({ folder: pluginFolder, name: 'package.json' })

	// Check if the package.json file is valid
	const parsedJSON = parsePluginPackageJSON(packageJSON)

	if (typeof parsedJSON === 'string') {
		console.error(parsedJSON)
		return
	}

	const pluginFolderName = parsedJSON.name

	// Create the plugin folder if it doesn't exist
	const targetFolder = join(pluginFolderPath, pluginFolderName)
	await fs.mkdir(targetFolder, { recursive: true })

	// Copy the folder from the given path to the plugin folder
	await fs.cp(pluginFolder, targetFolder, { recursive: true })

	// Build the docker container for the plugin
	if (parsedJSON.dockerCompose) {
		await buildDockerCompose({
			cwd: targetFolder,
			config: join(targetFolder, parsedJSON.dockerCompose),
			onError: (err) => {
				console.error(
					`An error occurred while building plugin ${parsedJSON.pluginName}'s Dockerfile:`,
					err
				)
			}
		})
	}
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

export type PluginDetail = {
	id: string
	name: string
	indexPath: string
	iconPath?: string
}

export async function startAllPlugins(): Promise<PluginDetail[]> {
	const pluginFolder = await getPluginFolder()
	const plugins = await getPluginList(pluginFolder, true)

	const dockerCheck = await checkDocker()
	let alerted = false

	const pluginDetails: PluginDetail[] = []

	plugins.forEach(async (plugin) => {
		const json = plugin.json

		if (!json) return

		// Try to start the docker container
		if (json.dockerCompose) {
			if (!dockerCheck.available) {
				console.error(dockerCheck.error)

				if (!alerted) {
					dialog.showErrorBox(
						'Docker Not Found',
						`Docker was not found on your system. Start Docker if it is installed, otherwise please install Docker to use Ouroboros with plugin "${json.pluginName}".`
					)
					alerted = true
				}
			} else {
				startDockerCompose({
					cwd: join(plugin.folder),
					config: join(plugin.folder, json.dockerCompose),
					onError: (err) => {
						console.log(
							`An error occurred while starting plugin ${json.pluginName}'s Dockerfile:`,
							err
						)
					}
				})
			}
		}

		const localPluginDetails: PluginDetail = {
			id: json.name,
			name: json.pluginName,
			indexPath: getPluginFileURL(plugin.folderName, json.index)
		}

		// Get the icons
		if (json.icon) {
			const pathToIcon = getPluginFileURL(plugin.folderName, json.icon)
			localPluginDetails.iconPath = pathToIcon
		}

		pluginDetails.push(localPluginDetails)
	})

	return pluginDetails
}

export async function stopAllPlugins(): Promise<void> {
	const pluginFolder = await getPluginFolder()
	const plugins = await getPluginList(pluginFolder, true)

	// Stop all plugins at the same time
	await Promise.all(
		plugins.map(async (plugin) => {
			const json = plugin.json

			if (!json) return

			// Try to stop the docker container
			if (json.dockerCompose) {
				try {
					await stopDockerCompose({
						cwd: join(plugin.folder),
						config: join(plugin.folder, json.dockerCompose)
					})
				} catch (err) {
					console.log(
						`An error occurred while stopping plugin ${json.pluginName}'s Dockerfile:`,
						err
					)
				}
			}
		})
	)
}
