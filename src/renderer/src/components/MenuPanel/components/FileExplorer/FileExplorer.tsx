import Header from '@renderer/components/Header/Header'
import styles from './FileExplorer.module.css'
import FileEntry from './components/FileEntry/FileEntry'
import { DragOverlay } from '@dnd-kit/core'
import { useContext } from 'react'
import DraggableEntry from './components/DraggableEntry/DraggableEntry'
import { DragContext } from '@renderer/contexts/DragContext/DragContext'
import { DirectoryContext } from '@renderer/contexts/DirectoryContext/Directory'

function FileExplorer(): JSX.Element {
	const { active } = useContext(DragContext)

	const { files, isFolder, directoryName } = useContext(DirectoryContext)

	const fileEntries = files.map((file: string, i: number) => {
		// Determine the type of the file
		const type = isFolder[i] ? 'folder' : file.endsWith('.tif') ? 'image' : 'file'

		return <DraggableEntry name={file} path={`./${file}`} key={`./${file}`} type={type} />
	})

	// TODO: Header should be the folder name
	return (
		<>
			<div className={styles.fileExplorerPanel}>
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
