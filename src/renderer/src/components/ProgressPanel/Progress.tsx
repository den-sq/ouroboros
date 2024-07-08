import { useContext, useEffect, useState } from 'react'
import Header from '../Header/Header'
import ProgressBar from './components/ProgressBar/ProgressBar'
import ServerConnectedIndicator from './components/ServerConnectedIndicator/ServerConnectedIndicator'
import { ServerContext } from '../../contexts/ServerContext/ServerContext'
import { DirectoryContext } from '@renderer/contexts/DirectoryContext/DirectoryContext'
import { AlertContext } from '@renderer/contexts/AlertContext/AlertContext'

function ProgressPanel(): JSX.Element {
	const { refreshDirectory } = useContext(DirectoryContext)
	const {
		connected,
		performFetch,
		fetchResults,
		performStream,
		streamResults,
		streamDone,
		streamError
	} = useContext(ServerContext)
	const { addAlert } = useContext(AlertContext)

	const [progress, setProgress] = useState<any>(null)

	// Listen to the status stream for the active task
	useEffect(() => {
		if (fetchResults && 'task_id' in fetchResults) {
			performStream('/status_stream', fetchResults)
		}
	}, [fetchResults])

	// Update the progress state when new data is received
	useEffect(() => {
		if (streamResults && 'progress' in streamResults) {
			if (!('error' in streamResults && streamResults.error)) {
				setProgress(streamResults.progress)
			}
		}
	}, [streamResults])

	// Refresh the file list when the task is done
	useEffect(() => {
		if (streamDone && !streamError?.status) {
			addAlert('Task completed successfully!', 'success')
			refreshDirectory()

			// Delete the task from the server
			if (fetchResults && 'task_id' in fetchResults) {
				performFetch('/delete/', fetchResults, { method: 'POST' })
			}
		} else if (streamError?.status) {
			addAlert(streamError.message, 'error')
			refreshDirectory()

			// Delete the task from the server
			if (fetchResults && 'task_id' in fetchResults) {
				performFetch('/delete/', fetchResults, { method: 'POST' })
			}
		}
	}, [streamDone, streamError])

	const progressBars =
		!streamError?.status && progress
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
