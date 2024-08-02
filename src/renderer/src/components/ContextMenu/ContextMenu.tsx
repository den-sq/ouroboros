import styles from './ContextMenu.module.css'

export type ContextMenuAction = {
	label: string
	onClick: () => void
}

function ContextMenu({
	x,
	y,
	actions
}: {
	x: number
	y: number
	actions: ContextMenuAction[]
}): JSX.Element {
	return (
		<div
			className={`poppins-light ${styles.contextMenu}`}
			style={{ top: `${y}px`, left: `${x}px` }}
		>
			<ul className={styles.options}>
				{actions.map((action: ContextMenuAction, index: number) => (
					<li key={index} onClick={action.onClick}>
						{action.label}
					</li>
				))}
			</ul>
		</div>
	)
}

export default ContextMenu
