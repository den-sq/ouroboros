import { createContext, useEffect, useState } from 'react'

export const DirectoryContext = createContext(null as any)

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

		return () => {
			window.electron.ipcRenderer.removeAllListeners('selected-folder')
		}
	}, [])

	const refreshDirectory = () => {
		window.electron.ipcRenderer
			.invoke('fetch-folder-contents', directoryPath)
			.then(({ files, isFolder }) => {
				setFiles(files satisfies string[])
				setIsFolder(isFolder satisfies boolean[])
			})
	}

	useEffect(() => {
		refreshDirectory()
	}, [directoryPath])

	return (
		<DirectoryContext.Provider
			value={{ files, isFolder, directoryPath, directoryName, refreshDirectory }}
		>
			{children}
		</DirectoryContext.Provider>
	)
}

export default DirectoryProvider
