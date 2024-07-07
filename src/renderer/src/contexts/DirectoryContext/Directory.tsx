import { createContext, useEffect, useState } from 'react'

export const DirectoryContext = createContext(null as any)

function Directory({ children }) {
	const [directoryName, setDirectoryName] = useState(null)
	const [directoryPath, setDirectoryPath] = useState(null)
	const [files, setFiles] = useState<string[]>([])
	const [isFolder, setIsFolder] = useState<boolean[]>([])

	window.electron.ipcRenderer.on('selected-folder', (_, directory) => {
		if (!directory || directory.length === 0) return

		setDirectoryPath(directory)

		// Clean up the directory name
		const directorySplit = directory.split('/')
		setDirectoryName(directorySplit[directorySplit.length - 1])
	})

	useEffect(() => {
		window.electron.ipcRenderer
			.invoke('fetch-folder-contents', directoryPath)
			.then(({ files, isFolder }) => {
				setFiles(files satisfies string[])
				setIsFolder(isFolder satisfies boolean[])
			})
	}, [directoryPath])

	return (
		<DirectoryContext.Provider value={{ files, isFolder, directoryPath, directoryName }}>
			{children}
		</DirectoryContext.Provider>
	)
}

export default Directory
