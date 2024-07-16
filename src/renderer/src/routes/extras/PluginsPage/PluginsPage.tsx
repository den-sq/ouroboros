import Header from '@renderer/components/Header/Header'

import styles from './PluginsPage.module.css'
import PluginMenuButton from './components/PluginMenu/PluginMenuButton'

import TrashIcon from './assets/trash.svg?react'
import AddIcon from './assets/plus.svg?react'
import PluginItem from './components/PluginItem/PluginItem'
import { useEffect, useState } from 'react'

function PluginsPage(): JSX.Element {
	const [selectedPlugins, setSelectedPlugins] = useState<Set<string>>(new Set())

	const [pluginFolderContents, setPluginFolderContents] = useState<string[]>([])

	useEffect(() => {
		window.electron.ipcRenderer.send('get-plugin-folder-contents')

		window.electron.ipcRenderer.on('plugin-folder-contents', (_, arg) => {
			setPluginFolderContents(arg)
		})

		return (): void => {
			window.electron.ipcRenderer.removeAllListeners('plugin-folder-contents')
		}
	}, [])

	return (
		<div className={styles.mainPluginArea}>
			<Header text={'Plugins'} />
			<div className={styles.pluginMenuArea}>
				<PluginMenuButton icon={<TrashIcon />} onClick={() => {}} />
				<PluginMenuButton icon={<AddIcon />} onClick={() => {}} />
			</div>
			<div className={styles.pluginItemArea}>
				{pluginFolderContents.map((plugin) => {
					return (
						<PluginItem
							name={plugin}
							id={plugin}
							key={plugin}
							selectedPlugins={selectedPlugins}
							setSelectedPlugins={setSelectedPlugins}
						/>
					)
				})}
			</div>
		</div>
	)
}

export default PluginsPage
