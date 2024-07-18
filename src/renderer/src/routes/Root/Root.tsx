import MenuPanel from '@renderer/components/MenuPanel/MenuPanel'
import AlertProvider from '@renderer/contexts/AlertContext'
import DirectoryProvider from '@renderer/contexts/DirectoryContext'
import DragProvider from '@renderer/contexts/DragContext'
import ServerProvider from '@renderer/contexts/ServerContext'
import { Outlet } from 'react-router-dom'

import styles from './Root.module.css'
import TestingPluginProvider from '@renderer/contexts/TestingPluginContext'

function Root(): JSX.Element {
	return (
		<>
			<TestingPluginProvider>
				<AlertProvider>
					<ServerProvider>
						<DirectoryProvider>
							<DragProvider>
								<div className={styles.rootArea}>
									<MenuPanel />
									<Outlet />
								</div>
							</DragProvider>
						</DirectoryProvider>
					</ServerProvider>
				</AlertProvider>
			</TestingPluginProvider>
		</>
	)
}

export default Root
