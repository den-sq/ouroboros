import { RouterProvider } from 'react-router-dom'

import { router } from './router'
import { useEffect } from 'react'

function App(): JSX.Element {
	useEffect(() => {
		window.electron.ipcRenderer.send('get-plugin-paths')
	}, [])

	return (
		<>
			<RouterProvider router={router} />
		</>
	)
}

export default App
