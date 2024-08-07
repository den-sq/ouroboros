export const writeFile = async (folder: string, name: string, data: string): Promise<boolean> => {
	return await window.electron.ipcRenderer.invoke('save-file', { folder, name, data })
}

export const newFolder = async (folder: string): Promise<boolean> => {
	return await window.electron.ipcRenderer.invoke('save-file', { folder, name: '', data: '' })
}

export const join = async (...args: string[]): Promise<string> => {
	return window.electron.ipcRenderer.invoke('join-path', args)
}

export const joinWithSeparator = (separator: string, ...args: string[]): string => {
	return args.join(separator)
}

export const readFile = async (folder: string, name: string): Promise<string> => {
	return window.electron.ipcRenderer.invoke('read-file', { folder, name })
}

export const deleteFSItem = async (path: string): Promise<void> => {
	return window.electron.ipcRenderer.invoke('delete-fs-item', path)
}

export const renameFSItem = async (oldPath: string, newPath: string): Promise<void> => {
	return window.electron.ipcRenderer.invoke('rename-fs-item', { oldPath, newPath })
}

export const moveFSItem = async (oldPath: string, newPath: string): Promise<void> => {
	return renameFSItem(oldPath, newPath)
}

export const assumeSeparator = (path: string): string => {
	return path.includes('/') ? '/' : '\\'
}

export const basename = (path: string): string => {
	return path.split(assumeSeparator(path)).pop() || ''
}

export const directory = (path: string): string => {
	const separator = assumeSeparator(path)

	return path.split(separator).slice(0, -1).join(separator)
}

export const isPathFile = (path: string): boolean => {
	return basename(path).includes('.')
}
