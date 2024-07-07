import { useContext, useEffect, useState } from 'react'
import Header from '../Header/Header'
import ProgressBar from './components/ProgressBar/ProgressBar'
import ServerConnectedIndicator from './components/ServerConnectedIndicator/ServerConnectedIndicator'
import { ServerContext } from '../../contexts/ServerContext/ServerContext'
import { DirectoryContext } from '@renderer/contexts/DirectoryContext/DirectoryContext'
import { AlertContext } from '@renderer/contexts/AlertContext/AlertContext'

function ProgressPanel(): JSX.Element {
	const { refreshDirectory } = useContext(DirectoryContext)
	const { connected, activeID, useStream } = useContext(ServerContext)
	const { addAlert } = useContext(AlertContext)

	const [runStream, setRunStream] = useState(false)
	const [query, setQuery] = useState({})
	const { data, done, error } = useStream('/status_stream', query, runStream)

	const [progress, setProgress] = useState<any>(null)

	// Listen to the status stream for the active task
	useEffect(() => {
		if (activeID) {
			setQuery({ task_id: activeID })
			setRunStream(true)
		}
	}, [activeID])

	// Update the progress state when new data is received
	useEffect(() => {
		if (data && 'progress' in data) {
			if (!('error' in data && data.error)) {
				setProgress(data.progress)
			}
		}
	}, [data])

	// Refresh the file list when the task is done
	useEffect(() => {
		if (done && !error?.status) {
			addAlert('Task completed successfully!', 'success')
			refreshDirectory()
		} else if (error?.status) {
			addAlert(error.message, 'error')
			refreshDirectory()
		}
	}, [done, error])

	const progressBars =
		!error?.status && progress
			? progress.map((p: any, i: number) => {
					const [name, _progress] = p
					return <ProgressBar key={i} progress={_progress * 100} name={name} />
				})
			: null

	return (
		<div className="panel">
			<Header text={'Progress'} />
			<ServerConnectedIndicator connected={connected} />
			{progressBars}
		</div>
	)
}

export default ProgressPanel
