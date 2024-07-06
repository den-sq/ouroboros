import OptionsPanel from '@renderer/components/OptionsPanel/OptionsPanel'
import styles from './SlicesPage.module.css'
import VisualizePanel from '@renderer/components/VisualizePanel/VisualizePanel'
import ProgressPanel from '@renderer/components/ProgressPanel/Progress'
import ServerConnection from '@renderer/components/ServerConnection/ServerConnection'

function SlicesPage(): JSX.Element {
	return (
		<ServerConnection>
			<div className={styles.slicePage}>
				<VisualizePanel />
				<ProgressPanel />
				<OptionsPanel />
			</div>
		</ServerConnection>
	)
}

export default SlicesPage
