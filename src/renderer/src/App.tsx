import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom'

import SlicesPage from './routes/SlicesPage/SlicesPage'
import BackprojectPage from './routes/BackprojectPage/BackprojectPage'
import Root from './routes/Root/Root'
import ServerProvider from './contexts/ServerContext/ServerContext'

const router = createBrowserRouter([
	{
		path: '/',
		element: <Root />,
		children: [
			{
				path: '/',
				element: <Navigate to="/slice" />
			},
			{
				path: '/slice',
				element: (
					<ServerProvider>
						<SlicesPage />
					</ServerProvider>
				)
			},
			{
				path: '/backproject',
				element: (
					<ServerProvider>
						<BackprojectPage />
					</ServerProvider>
				)
			}
		]
	}
])

function App(): JSX.Element {
	return (
		<>
			<RouterProvider router={router} />
		</>
	)
}

export default App
