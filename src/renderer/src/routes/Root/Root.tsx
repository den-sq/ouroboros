import MenuPanel from '@renderer/components/MenuPanel/MenuPanel'
import AlertProvider from '@renderer/contexts/AlertContext/AlertContext'
import DirectoryProvider from '@renderer/contexts/DirectoryContext/DirectoryContext'
import DragProvider from '@renderer/contexts/DragContext/DragContext'
// import ServerProvider from '@renderer/contexts/ServerContext/ServerContext'
import { Outlet } from 'react-router-dom'

function Root(): JSX.Element {
	return (
		<>
			<AlertProvider>
				{/* <ServerProvider> */}
				<DirectoryProvider>
					<DragProvider>
						<MenuPanel />
						<Outlet />
					</DragProvider>
				</DirectoryProvider>
				{/* </ServerProvider> */}
			</AlertProvider>
		</>
	)
}

export default Root
