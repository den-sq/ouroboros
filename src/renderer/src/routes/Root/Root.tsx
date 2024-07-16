import MenuPanel from '@renderer/components/MenuPanel/MenuPanel'
import AlertProvider from '@renderer/contexts/AlertContext'
import DirectoryProvider from '@renderer/contexts/DirectoryContext'
import DragProvider from '@renderer/contexts/DragContext'
import ServerProvider from '@renderer/contexts/ServerContext'
import { Outlet } from 'react-router-dom'

import styles from './Root.module.css'

function Root(): JSX.Element {
	return (
		<>
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
		</>
	)
}

export default Root
