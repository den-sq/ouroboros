import { createContext, useCallback, useEffect, useState } from 'react'

export type DirectoryContextValue = {
	files: string[]
	isFolder: boolean[]
	directoryPath: string | null
	directoryName: string | null
}

export const DirectoryContext = createContext<DirectoryContextValue>(null as any)

function DirectoryProvider({ children }) {
	const [directoryName, setDirectoryName] = useState(null)
	const [directoryPath, setDirectoryPath] = useState(null)
	const [files, setFiles] = useState<string[]>([])
	const [isFolder, setIsFolder] = useState<boolean[]>([])

	useEffect(() => {
		window.electron.ipcRenderer.on('selected-folder', (_, directory) => {
			if (!directory || directory.length === 0) return

			setDirectoryPath(directory)

			// Clean up the directory name
			const directorySplit = directory.split('/')
			setDirectoryName(directorySplit[directorySplit.length - 1])
		})

		window.electron.ipcRenderer.on('folder-contents-update', (_, { files, isFolder }) => {
			setFiles(files)
			setIsFolder(isFolder)
		})

		return () => {
			window.electron.ipcRenderer.removeAllListeners('selected-folder')
			window.electron.ipcRenderer.removeAllListeners('folder-contents-update')
		}
	}, [])

	const refreshDirectory = useCallback(() => {
		window.electron.ipcRenderer
			.invoke('fetch-folder-contents', directoryPath)
			.then(({ files, isFolder }) => {
				setFiles(files satisfies string[])
				setIsFolder(isFolder satisfies boolean[])
			})
	}, [directoryPath])

	useEffect(() => {
		refreshDirectory()
	}, [directoryPath])

	return (
		<DirectoryContext.Provider value={{ files, isFolder, directoryPath, directoryName }}>
			{children}
		</DirectoryContext.Provider>
	)
}

export default DirectoryProvider
