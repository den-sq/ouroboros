import { useContext, useEffect, useState } from 'react'
import Header from '../Header/Header'
import ProgressBar from './components/ProgressBar/ProgressBar'
import ServerConnectedIndicator from './components/ServerConnectedIndicator/ServerConnectedIndicator'
import { ServerContext } from '../../contexts/ServerConnection/ServerConnection'

function ProgressPanel(): JSX.Element {
	const { connected, activeID, useStream } = useContext(ServerContext)

	const [runStream, setRunStream] = useState(false)
	const [query, setQuery] = useState({})
	const { data, error } = useStream('/status_stream', query, runStream)

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
			setProgress(data.progress)
		}
	}, [data])

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
