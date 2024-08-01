import Header from '@renderer/components/Header/Header'
import styles from './FileExplorer.module.css'
import FileEntry from './components/FileEntry/FileEntry'
import { DragOverlay } from '@dnd-kit/core'
import { useContext } from 'react'
import DraggableEntry from './components/DraggableEntry/DraggableEntry'
import { DragContext } from '@renderer/contexts/DragContext'
import { DirectoryContext } from '@renderer/contexts/DirectoryContext'

function FileExplorer(): JSX.Element {
	const { active } = useContext(DragContext)

	const { nodes, directoryName } = useContext(DirectoryContext)

	const fileEntries = nodes
		? Object.entries(nodes).map(([, node]) => {
				return <DraggableEntry node={node} key={node.path} />
			})
		: null

	return (
		<>
			<div className={styles.fileExplorerPanel}>
				<div className={styles.fileExplorerInnerPanel}>
					{directoryName ? (
						<>
							<Header text={directoryName} />
							<div>{fileEntries}</div>
						</>
					) : (
						<>
							<Header text={'Files'} />
							<div className={`poppins-medium ${styles.helpText}`}>
								File &gt; Open Folder
							</div>
						</>
					)}
				</div>
			</div>
			<DragOverlay>
				{active && active.data.current ? (
					<FileEntry
						name={active.data.current.name}
						path={active.data.current.path}
						type={active.data.current.type}
					/>
				) : null}
			</DragOverlay>
		</>
	)
}

export default FileExplorer
