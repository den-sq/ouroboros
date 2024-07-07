import MenuPanel from './components/MenuPanel/MenuPanel'
import SlicesPage from './routes/SlicesPage/SlicesPage'

import Directory from './contexts/DirectoryContext/Directory'
import Drag from './contexts/DragContext/DragContext'

function App(): JSX.Element {
	return (
		<>
			<Directory>
				<Drag>
					<MenuPanel />
					<SlicesPage />
				</Drag>
			</Directory>
		</>
	)
}

export default App
