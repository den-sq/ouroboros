import { BrowserWindow, IpcMain } from 'electron'
import { rename, rm, stat } from 'fs/promises'
import { sep } from 'path'
import Watcher from 'watcher'

import { readFile, saveFile } from '../helpers'
import { basename, join } from 'path'

type FSEvent = {
	event: string
	directoryPath: string
	targetPath: string
	targetPathNext: string
	isDirectory: boolean
	pathParts: string[]
	nextPathParts: string[]
	relativePath: string
	relativePathNext: string
	separator: string
}

export const addFSEventHandlers = (ipcMain: IpcMain, getMainWindow: () => BrowserWindow): void => {
	let subscription: Watcher | null = null

	// Fetch the contents of the given folder
	ipcMain.handle('fetch-folder-contents', async (_, folderPath: string) => {
		if (folderPath === '' || folderPath === undefined || folderPath === null) return

		if (subscription) {
			subscription.close()
			subscription = null
		}

		// Send updates to the renderer when the folder contents change
		subscription = new Watcher(folderPath, { recursive: true, renameDetection: true })

		subscription.on('all', async (event, targetPath, targetPathNext) => {
			// eslint-disable-next-line no-useless-escape
			if (/(^|\/)\.[^\/\.]/g.test(targetPath)) return

			let isDirectory = false

			const isRename = (event === 'rename' || event === 'renameDir') && targetPathNext
			const isAddLike = event === 'add' || event === 'change' || event === 'addDir'

			// Check if the target path is a directory
			if (isRename) {
				const stats = await stat(targetPathNext)
				isDirectory = stats.isDirectory()
			} else if (isAddLike) {
				const stats = await stat(targetPath)
				isDirectory = stats.isDirectory()
			}

			const relativePath = targetPath.replace(folderPath, '').replace(/^[\/\\]/, '')

			let relativePathNext = ''
			if (targetPathNext) {
				relativePathNext = targetPathNext.replace(folderPath, '').replace(/^[\/\\]/, '')
			}

			// Make sure the path is not the root folder
			if (relativePath === '' || relativePath.length === 0) return

			// Split the path by the separator
			const pathParts = relativePath.split(sep)
			const nextPathParts = relativePathNext.split(sep)

			const fsEvent: FSEvent = {
				directoryPath: folderPath,
				event,
				targetPath,
				targetPathNext,
				isDirectory,
				pathParts,
				nextPathParts,
				relativePath,
				relativePathNext,
				separator: sep
			}

			if (getMainWindow && getMainWindow()) {
				getMainWindow().webContents.send('folder-contents-update', fsEvent)
			}
		})
	})

	// Save a string to a file
	ipcMain.handle('save-file', async (_, args) => {
		return await saveFile(args)
	})

	// Join two paths
	ipcMain.handle('join-path', (_, args: string[]) => {
		return join(...args)
	})

	// Get base name of a path
	ipcMain.handle('basename-path', (_, { folder }) => {
		return basename(folder)
	})

	// Read the contents of a file as a string
	ipcMain.handle('read-file', async (_, args) => {
		return await readFile(args)
	})

	// Delete a file or folder
	ipcMain.handle('delete-fs-item', async (_, path: string) => {
		try {
			await rm(path, {
				recursive: true
			})
		} catch (error) {
			console.error(error)
		}
	})

	// Rename a file or folder
	ipcMain.handle('rename-fs-item', async (_, { oldPath, newPath }) => {
		try {
			await rename(oldPath, newPath)
		} catch (error) {
			console.error(error)
		}
	})
}
