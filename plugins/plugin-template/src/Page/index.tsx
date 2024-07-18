import { useEffect, useState } from 'react'
import styles from './styles.module.css'

// NOTE: Change the PORT to the port of the server from the backend
// The app's server is running on port 8000, so use a different port
// that is not being used by the app or any other plugins
const PORT = 8001

function TemplatePage(): JSX.Element {
	const [testResult, setTestResult] = useState<string>('')

	useEffect(() => {
		const runFetch = () => {
			fetch(`http://localhost:${PORT}/`)
				.then((res) => res.text())
				.then((data) => setTestResult(data))
				.catch(() => setTimeout(runFetch, 1000))
		}

		if (testResult === '') {
			runFetch()
		}
	}, [])

	return (
		<div>
			<h1 className={styles.header}>{testResult === '' ? 'Template Page!' : testResult}</h1>
		</div>
	)
}

export default TemplatePage
