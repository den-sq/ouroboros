import OptionsPanel from '@renderer/components/OptionsPanel/OptionsPanel'
import styles from './SlicesPage.module.css'
import VisualizePanel from '@renderer/components/VisualizePanel/VisualizePanel'
import ProgressPanel from '@renderer/components/ProgressPanel/Progress'

function SlicesPage(): JSX.Element {
	return (
		<div className={styles.slicePage}>
			<VisualizePanel />
			<ProgressPanel />
			<OptionsPanel />
		</div>
	)
}

export default SlicesPage
