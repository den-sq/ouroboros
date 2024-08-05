import Logger from 'electron-log'
import log from 'electron-log/main'

const scopes: { [key: string]: Logger.LogFunctions } = {}

export const initLogging = (): Logger.MainLogger => {
	log.initialize()

	console.log = log.info
	console.error = log.error
	console.warn = log.warn
	console.info = log.info

	return log
}

export const scope = (loggingScope: string): Logger.LogFunctions => {
	if (!scopes[loggingScope]) {
		scopes[loggingScope] = log.scope(loggingScope)
	}

	return scopes[loggingScope]
}
