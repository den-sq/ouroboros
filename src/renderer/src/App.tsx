import MenuPanel from './components/MenuPanel/MenuPanel'
import SlicesPage from './routes/SlicesPage/SlicesPage'

import DirectoryProvider from './contexts/DirectoryContext/DirectoryContext'
import DragProvider from './contexts/DragContext/DragContext'
import AlertProvider from './contexts/AlertContext/AlertContext'

function App(): JSX.Element {
	return (
		<>
			<AlertProvider>
				<DirectoryProvider>
					<DragProvider>
						<MenuPanel />
						<SlicesPage />
					</DragProvider>
				</DirectoryProvider>
			</AlertProvider>
		</>
	)
}

export default App
