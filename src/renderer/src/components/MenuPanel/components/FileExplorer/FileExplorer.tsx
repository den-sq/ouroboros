import Header from '@renderer/components/Header/Header'
import styles from './FileExplorer.module.css'
import FileEntry from './components/FileEntry/FileEntry'
import { DragOverlay } from '@dnd-kit/core'
import { MouseEvent, useCallback, useContext, useState } from 'react'
import DraggableEntry from './components/DraggableEntry/DraggableEntry'
import { DragContext } from '@renderer/contexts/DragContext'
import { DirectoryContext, FileSystemNode } from '@renderer/contexts/DirectoryContext'
import useContextMenu from '@renderer/hooks/use-context-menu'
import ContextMenu, { ContextMenuAction } from '@renderer/components/ContextMenu/ContextMenu'
import { deleteFSItem, join, newFolder, renameFSItem } from '@renderer/interfaces/file'

function FileExplorer(): JSX.Element {
	const { active } = useContext(DragContext)
	const { nodes, directoryName, directoryPath } = useContext(DirectoryContext)
	const { point, clicked, data, handleContextMenu } = useContextMenu<FileSystemNode>()

	const [renamePath, setRenamePath] = useState<string | null>(null)

	const handleRenameChange = useCallback(
		(event: InputEvent): void => {
			const value = (event.target as HTMLInputElement).value

			if (value === '') return
			if (!data) return

			const oldPath = data.path
			const newPath = data.path.replace(data.name, value)

			if (oldPath === newPath) {
				// Reset the rename path
				setRenamePath(null)
				return
			}

			renameFSItem(oldPath, newPath)

			// Rename the file
			setRenamePath(null)
		},
		[renamePath, setRenamePath, data]
	)

	const fileEntries = nodes
		? Object.entries(nodes).map(([, node]) => {
				return (
					<DraggableEntry
						node={node}
						key={node.path}
						handleContextMenu={handleContextMenu}
						editPath={renamePath}
						handleChange={handleRenameChange}
					/>
				)
			})
		: null

	const backgroundContextActions: ContextMenuAction[] = [
		{
			label: 'New Folder',
			onClick: async (): Promise<void> => {
				if (!data || data.children == undefined) return

				let name = 'untitled folder'

				const isUsed = (name: string): boolean => {
					return Object.values(data.children!).some((node) => node.name === name)
				}

				// Find a unique name
				let i = 1

				while (isUsed(name)) {
					name = `untitled folder ${i}`
					i++
				}

				const folderPath = await join(data.path, name)

				newFolder(folderPath)
			}
		}
	]

	const fileContextActions: ContextMenuAction[] = [
		{
			label: 'Rename',
			onClick: (): void => {
				if (!data) return

				setRenamePath(data.path)
			}
		},
		{
			label: 'Delete',
			onClick: (): void => {
				if (!data) return

				deleteFSItem(data.path)
			}
		}
	]

	const folderContextActions: ContextMenuAction[] = [
		...backgroundContextActions,
		...fileContextActions
	]

	const contextActions =
		data?.name === directoryName
			? backgroundContextActions
			: data?.children
				? folderContextActions
				: fileContextActions

	return (
		<>
			{clicked && <ContextMenu {...point} actions={contextActions} />}
			<div className={styles.fileExplorerPanel}>
				<div
					className={styles.fileExplorerInnerPanel}
					onContextMenu={(e) => {
						if (!directoryName || !directoryPath) return

						const data: FileSystemNode = {
							name: directoryName,
							path: directoryPath,
							children: nodes
						}

						handleContextMenu(e as MouseEvent, data)
					}}
				>
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
