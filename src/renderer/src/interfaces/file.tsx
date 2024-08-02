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
