import { join } from 'path'
import { startDockerCompose, stopDockerCompose } from './docker'

export async function startMainServerDevelopment(): Promise<void> {
	try {
		await startDockerCompose({
			cwd: join(__dirname, '../../python/'),
			config: 'compose.yml',
			onError: (err) => {
				console.error('An error occurred while starting the main server:', err)
			}
		})
	} catch (error) {
		console.error('An error occurred while starting the main server:', error)
	}
}

export async function stopMainServerDevelopment(): Promise<void> {
	await stopDockerCompose({
		cwd: join(__dirname, '../../python/'),
		config: 'compose.yml'
	})
}
