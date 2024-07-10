export const writeFile = async (folder: string, name: string, data: string): Promise<boolean> => {
	return await window.electron.ipcRenderer.invoke('save-file', { folder, name, data })
}

export const join = async (folder: string, name: string): Promise<string> => {
	return window.electron.ipcRenderer.invoke('join-path', { folder, name })
}

export const readFile = async (folder: string, name: string): Promise<string> => {
	return window.electron.ipcRenderer.invoke('read-file', { folder, name })
}
