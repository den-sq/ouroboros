import { useDraggable } from '@dnd-kit/core'
import FileEntry from '../FileEntry/FileEntry'
import { FileSystemNode } from '@renderer/contexts/DirectoryContext'

import styles from './DraggableEntry.module.css'
import { MouseEvent, useState } from 'react'

function DraggableEntry({
	node,
	handleContextMenu
}: {
	node: FileSystemNode
	handleContextMenu: (event: MouseEvent, data?: FileSystemNode | undefined) => void
}): JSX.Element {
	// Determine the type of the entry
	const type = node.children ? 'folder' : node.name.endsWith('.tif') ? 'image' : 'file'
	const isFolder = type === 'folder'
	const isEmpty = !node.children || Object.keys(node.children).length === 0

	const [isCollapsed, setIsCollapsed] = useState(true)

	const { attributes, listeners, setNodeRef } = useDraggable({
		id: node.path,
		data: {
			name: node.name,
			path: node.path,
			type,
			source: 'file-explorer'
		}
	})

	return (
		<div>
			<div
				className={isFolder ? (isEmpty ? styles.emptyFolder : styles.folder) : styles.file}
			>
				{!isEmpty && (
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 320 512"
						className={`${styles.collapseIcon} ${isCollapsed ? '' : styles.collapseIconOpen}`}
						onClick={() => setIsCollapsed((prev) => !prev)}
					>
						<path
							fill="currentColor"
							d="M137.4 374.6c12.5 12.5 32.8 12.5 45.3 0l128-128c9.2-9.2 11.9-22.9 6.9-34.9s-16.6-19.8-29.6-19.8L32 192c-12.9 0-24.6 7.8-29.6 19.8s-2.2 25.7 6.9 34.9l128 128z"
						/>
					</svg>
				)}
				<div
					ref={setNodeRef}
					{...listeners}
					{...attributes}
					onContextMenu={(e) => {
						handleContextMenu(e as MouseEvent, node)
					}}
				>
					<FileEntry name={node.name} path={node.path} type={type} />
				</div>
			</div>
			{!isEmpty && !isCollapsed && node.children && (
				<div className={styles.children}>
					{Object.entries(node.children).map(([, child]) => (
						<DraggableEntry
							node={child}
							key={child.path}
							handleContextMenu={handleContextMenu}
						/>
					))}
				</div>
			)}
		</div>
	)
}

export default DraggableEntry
