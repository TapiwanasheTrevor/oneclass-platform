import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json', 'xml'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.test.{js,ts,jsx,tsx}',
        '**/*.spec.{js,ts,jsx,tsx}',
        '**/types/',
        '**/*.d.ts',
        'coverage/',
        'dist/',
        '.next/',
        'out/',
        'build/',
        'public/',
        'styles/',
        'tailwind.config.ts',
        'next.config.mjs',
        'postcss.config.mjs',
        'components.json'
      ],
      include: [
        'app/**/*.{js,ts,jsx,tsx}',
        'components/**/*.{js,ts,jsx,tsx}',
        'hooks/**/*.{js,ts,jsx,tsx}',
        'lib/**/*.{js,ts,jsx,tsx}',
        'utils/**/*.{js,ts,jsx,tsx}'
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80
      },
      all: true,
      skipFull: false
    },
    globals: true,
    threads: false,
    pool: 'forks',
    testTimeout: 10000,
    hookTimeout: 10000,
    teardownTimeout: 10000,
    bail: 1,
    logHeapUsage: true,
    allowOnly: true,
    passWithNoTests: false,
    watch: false,
    reporters: ['verbose', 'html', 'json'],
    outputFile: {
      html: './test-results/index.html',
      json: './test-results/results.json'
    },
    cache: {
      dir: './node_modules/.vitest'
    }
  },
  define: {
    'import.meta.vitest': undefined,
  },
  esbuild: {
    target: 'node14'
  }
})