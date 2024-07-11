import { createHashRouter, Navigate, RouterProvider } from 'react-router-dom'

import SlicesPage from './routes/SlicesPage/SlicesPage'
import BackprojectPage from './routes/BackprojectPage/BackprojectPage'
import Root from './routes/Root/Root'

const router = createHashRouter([
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
				element: <SlicesPage />
			},
			{
				path: '/backproject',
				element: <BackprojectPage />
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
