import Header from '@renderer/components/Header/Header'
import styles from './FileExplorer.module.css'
import FileEntry from './components/FileEntry/FileEntry'
import { DragOverlay } from '@dnd-kit/core'
import { useContext } from 'react'
import { DragContext } from '@renderer/App'
import DraggableEntry from './components/DraggableEntry/DraggableEntry'

function FileExplorer(): JSX.Element {
	const { active } = useContext(DragContext)

	const fileEntries = [
		<DraggableEntry
			name={'sample-backprojected'}
			path="./sample-backprojected"
			key="./sample-backprojected"
			type="folder"
		/>,
		<DraggableEntry
			name={'sample-backprojected.tif'}
			path="./sample-backprojected.tif"
			key="./sample-backprojected.tif"
			type="image"
		/>,
		<DraggableEntry
			name={'sample-configuration.json'}
			path="./sample-configuration.json"
			key="./sample-configuration.json"
			type="file"
		/>,
		<DraggableEntry
			name={'sample-slices'}
			path="./sample-slices"
			key="./sample-slices"
			type="folder"
		/>,
		<DraggableEntry name={'sample.tif'} path="./sample.tif" key="./sample.tif" type="image" />
	]

	// TODO: Header should be the folder name
	return (
		<>
			<div className={styles.fileExplorerPanel}>
				<Header text="Files" />
				<div>{fileEntries}</div>
			</div>
			<DragOverlay>
				{active ? (
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
