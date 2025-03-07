'use client'

import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { YAMLFileList } from '../../components/configuration/YAMLFileList'
import { FileUpload } from '../../components/configuration/FileUpload'

type YAMLType = 'catalogs' | 'packages' | 'senders'

export default function Configuration() {
  const [selectedTab, setSelectedTab] = useState<YAMLType>('catalogs')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Configuración</h1>
        <p className="text-gray-600">Gestión de archivos de configuración YAML</p>
      </div>

      <Tabs defaultValue="catalogs" className="w-full" onValueChange={(value) => setSelectedTab(value as YAMLType)}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="catalogs">Catálogos</TabsTrigger>
          <TabsTrigger value="packages">Paquetes</TabsTrigger>
          <TabsTrigger value="senders">Emisores</TabsTrigger>
        </TabsList>

        <div className="mt-6">
          <FileUpload type={selectedTab} />
        </div>

        <TabsContent value="catalogs">
          <YAMLFileList type="catalogs" />
        </TabsContent>

        <TabsContent value="packages">
          <YAMLFileList type="packages" />
        </TabsContent>

        <TabsContent value="senders">
          <YAMLFileList type="senders" />
        </TabsContent>
      </Tabs>
    </div>
  )
}