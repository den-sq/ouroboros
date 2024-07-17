/* eslint-disable */
// @ts-nocheck

import { createHashRouter, Navigate } from 'react-router-dom'

import SlicesPage from './routes/SlicesPage/SlicesPage'
import BackprojectPage from './routes/BackprojectPage/BackprojectPage'
import Root from './routes/Root/Root'
import PluginsPage from './routes/extras/PluginsPage/PluginsPage'
import StylesWrapper from './components/StylesWrapper/StylesWrapper'

const pluginDetails: {
	id: string
	name: string
	mainPath: string
	stylesPath?: string
	iconPath?: string
}[] = []

window.electron.ipcRenderer.on('plugin-paths', (_, paths) => {
	try {
		pluginDetails.length = 0
		pluginDetails.push(...paths)
	} catch (e) {
		console.error(e)
	}
})

export const router = createHashRouter(
	[
		{
			id: 'root',
			path: '/',
			element: <Root />,
			children: [
				{
					path: '/',
					element: <Navigate to="/slice" />
				},
				{
					path: '/slice',
					element: <SlicesPage />
				},
				{
					path: '/backproject',
					element: <BackprojectPage />
				}
			]
		},
		{
			path: '/extras',
			children: [
				{
					path: 'plugins',
					element: <PluginsPage />
				}
			]
		}
	],
	{
		async unstable_patchRoutesOnMiss({ path, patch }) {
			const errorRoute = {
				path: path,
				element: <></>
			}

			// Try to add the plugin route
			if (pluginDetails.length === 0) {
				patch('root', [errorRoute])
				return
			}

			let route = await getPluginRoute(path)

			if (!route) {
				patch('root', [errorRoute])
				return
			}

			patch('root', [route])
		}
	}
)

const getPluginRoute = async (route: string) => {
	// Find the plugin id from the route
	const pluginId = route.split('/').at(-1)

	// Find the plugin details from the plugin id
	const pluginDetail = pluginDetails.find((plugin) => plugin.id === pluginId)

	if (!pluginDetail) return null

	let exportedPlugin = null

	try {
		const mainPath = pluginDetail.mainPath

		// Load the plugin
		const plugin = await import(/* @vite-ignore */ mainPath)

		exportedPlugin = plugin.default
	} catch (e) {
		console.error(e)
		return null
	}

	if (!exportedPlugin) return null

	const stylesPath = pluginDetail.stylesPath

	return {
		path: route,
		element: <StylesWrapper stylesPath={stylesPath}>{plugin.default}</StylesWrapper>
	}
}
