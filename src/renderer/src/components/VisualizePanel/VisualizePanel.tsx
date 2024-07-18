// import styles from './VisualizePanel.module.css'

function VisualizePanel({ children }: { children?: any }): JSX.Element {
	return (
		<div className="panel">
			<div className="inner-panel">{children}</div>
		</div>
	)
}

export default VisualizePanel
