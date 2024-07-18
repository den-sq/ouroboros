import Header from '../Header/Header'
import ProgressBar from './components/ProgressBar/ProgressBar'
import ServerConnectedIndicator from './components/ServerConnectedIndicator/ServerConnectedIndicator'

function ProgressPanel({ progress, connected }): JSX.Element {
	const progressBars = progress
		? progress.map((p: any, i: number) => {
				const [name, _progress] = p
				return <ProgressBar key={i} progress={_progress * 100} name={name} />
			})
		: null

	return (
		<div className="panel">
			<div className="inner-panel">
				<Header text={'Progress'} />
				<ServerConnectedIndicator connected={connected} />
				{progressBars}
			</div>
		</div>
	)
}

export default ProgressPanel
