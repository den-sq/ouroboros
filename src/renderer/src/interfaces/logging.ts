import log from 'electron-log/renderer'

const scope = log.scope('renderer')

export const initLogging = (): void => {
	console.log = scope.info
	console.error = scope.error
	console.warn = scope.warn
	console.info = scope.info
}
