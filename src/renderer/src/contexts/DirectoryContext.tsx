import { joinWithSeparator } from '@renderer/interfaces/file'
import { createContext, useCallback, useEffect, useState } from 'react'

export type DirectoryContextValue = {
	nodes: NodeChildren
	directoryPath: string | null
	directoryName: string | null
}

export const DirectoryContext = createContext<DirectoryContextValue>(null as never)

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

export type FileSystemNode = {
	name: string
	path: string
	children?: NodeChildren
}

export type NodeChildren = {
	[key: string]: FileSystemNode
}

function DirectoryProvider({ children }: { children: React.ReactNode }): JSX.Element {
	const [directoryName, setDirectoryName] = useState<string | null>(null)
	const [directoryPath, setDirectoryPath] = useState<string | null>(null)
	const [nodes, setNodes] = useState<NodeChildren>({})

	useEffect(() => {
		const clearSelectedFolderListener = window.electron.ipcRenderer.on(
			'selected-folder',
			(_, directory) => {
				if (!directory || directory.length === 0) return

				setDirectoryPath(directory)

				// Clean up the directory name
				const directorySplit = directory.split(/[/\\]/)
				setDirectoryName(directorySplit[directorySplit.length - 1])

				// Clear the folder contents
				setNodes({})
			}
		)

		const clearFolderUpdateListener = window.electron.ipcRenderer.on(
			'folder-contents-update',
			async (_, fsEvent: FSEvent) => {
				setNodes((prev) => handleFSEvent(prev, fsEvent))
			}
		)

		return (): void => {
			clearSelectedFolderListener()
			clearFolderUpdateListener()
		}
	}, [])

	const refreshDirectory = useCallback(() => {
		window.electron.ipcRenderer.invoke('fetch-folder-contents', directoryPath)
	}, [directoryPath])

	useEffect(() => {
		refreshDirectory()
	}, [directoryPath])

	return (
		<DirectoryContext.Provider value={{ nodes, directoryPath, directoryName }}>
			{children}
		</DirectoryContext.Provider>
	)
}

export default DirectoryProvider

function handleFSEvent(nodes: NodeChildren, fsEvent: FSEvent): NodeChildren {
	if (!fsEvent) return nodes

	const {
		event,
		targetPath,
		targetPathNext,
		isDirectory,
		pathParts,
		nextPathParts,
		directoryPath,
		separator
	} = fsEvent

	if (event === 'change') return nodes

	// Create a copy of the nodes object
	const nodesCopy = { ...nodes }

	let parts = pathParts
	let currentPath = nodesCopy
	let path = targetPath

	const deletePath = (): void => {
		for (let i = 0; i < pathParts.length; i++) {
			const part = parts[i]

			if (i === parts.length - 1) {
				delete currentPath[part]
			}

			if (!currentPath[part] || currentPath[part].children === undefined) break

			currentPath = currentPath[part].children!
		}
	}

	if (['rename', 'renameDir', 'unlink', 'unlinkDir'].includes(event)) {
		// Recursively delete the old path
		deletePath()

		if (event === 'rename' || event === 'renameDir') {
			parts = nextPathParts
			path = targetPathNext
		} else return nodesCopy
	}

	currentPath = nodesCopy

	// Add the path to the nodes object
	for (let i = 0; i < pathParts.length; i++) {
		const part = parts[i]

		// If this is the last part of the path, add the node
		if (i === parts.length - 1 && !currentPath[part]) {
			currentPath[part] = {
				name: part,
				path: path,
				children: isDirectory ? {} : undefined
			}
		}

		// If the intermediate part does not exist, create it
		if (!currentPath[part]) {
			currentPath[part] = {
				name: part,
				path: joinWithSeparator(separator, directoryPath, ...parts.slice(0, i + 1)),
				children: {}
			}
		}

		// Move to the next part of the path
		currentPath = currentPath[part].children!
	}

	return nodesCopy
}
