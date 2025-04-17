import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <div className="container">
        <div className="row">
          <div className="col col--6">
            <div className={styles.heroContent}>
              <Heading as="h1" className="hero__title">
                {siteConfig.title}
              </Heading>
              <p className="hero__subtitle">{siteConfig.tagline}</p>
              <p className={styles.heroDescription}>
                Add voice to your AI tools and make your coding experience more 
                interactive, accessible, and engaging.
              </p>
              <div className={styles.buttons}>
                <Link
                  className="button button--primary button--lg"
                  to="/docs/welcome">
                  Get Started in 5min ⏱️
                </Link>
                <Link
                  className={styles.githubButton}
                  to="https://github.com/yourusername/chatty-mcp">
                  View on GitHub
                </Link>
              </div>
            </div>
          </div>
          <div className="col col--6">
            <div className={styles.heroImage}>
              <img 
                src="/videos/chatty-mcp-demo.gif" 
                alt="Chatty MCP screenshot" 
                className={styles.screenshot}
              />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

function LivelyCodingExperience() {
  return (
    <section className={styles.livelyExperience}>
      <div className="container">
        <div className="row">
          <div className="col col--6">
            <Heading as="h2">Bring Your AI Editor to Life</Heading>
            <p>
              Chatty MCP transforms your coding experience by adding a voice to your AI assistant. 
              Whether you're using Cursor, Cline, or any other MCP-compatible editor, Chatty MCP 
              provides spoken responses that make interactions more engaging and human-like.
            </p>
            <p>
              Imagine getting verbal confirmations when your code changes are complete, 
              hearing explanations of complex algorithms, or receiving spoken guidance 
              while you navigate through your projects. Chatty MCP makes your AI tools more 
              accessible and creates a more natural workflow.
            </p>
            <div className={styles.actionButton}>
              <Link
                className="button button--primary button--lg"
                to="/docs/welcome">
                See How It Works
              </Link>
            </div>
          </div>
          <div className="col col--6 text--center">
            <img 
              src="/img/mermaid-diagram.png" 
              alt="Chatty MCP workflow diagram" 
              className={styles.featureImage} 
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function DemoSection() {
  return (
    <section className={styles.demoSection}>
      <div className="container">
        <div className={styles.demoContainer}>
          <div className={styles.demoText}>
            <Heading as="h2">See Chatty MCP in Action</Heading>
            <p>
              Watch a quick demonstration of Chatty MCP enhancing the AI coding experience with voice feedback.
              Experience how verbal responses make coding more intuitive and engaging.
            </p>
            <ul className={styles.demoFeatures}>
              <li>Hear your AI assistant respond to queries</li>
              <li>Experience seamless integration with Cursor and Cline</li>
              <li>See how voice output improves workflow and accessibility</li>
            </ul>
          </div>
          <div className={styles.videoWrapper}>
            <video 
              src="/videos/chatty-mcp-demo.mp4" 
              controls
              preload="metadata"
              className={styles.demoVideo}
            >
              Your browser does not support the video tag.
            </video>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - Voice for your AI tools`}
      description="Enhance your AI coding experience with voice interactions through Chatty MCP">
      <HomepageHeader />
      <main>
        <LivelyCodingExperience />
        <DemoSection />
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
